const fs = require('node:fs');
const assert = require('node:assert/strict');
const {createRequire} = require('node:module');
const path=require('node:path');
if(!process.env.HERMES_SOURCE) throw new Error('Set HERMES_SOURCE to the upstream checkout with installed npm dependencies');
const req = createRequire(path.join(process.env.HERMES_SOURCE,'apps/desktop/package.json'));
const {JSDOM} = req('jsdom');
const dom = new JSDOM('<!doctype html><html><body></body></html>', {url:'http://localhost'});
for (const k of ['window','document','HTMLElement','HTMLInputElement','HTMLFormElement','Element','Node','NodeFilter','MutationObserver','CustomEvent','Event','MouseEvent','getComputedStyle']) global[k] = dom.window[k];
Object.defineProperty(global,'navigator',{value:dom.window.navigator, configurable:true});
global.requestAnimationFrame = fn=>setTimeout(fn,0);
global.cancelAnimationFrame = clearTimeout;
global.ResizeObserver = class {observe(){} unobserve(){} disconnect(){}};
const React = req('react');
const runtime = req('react/jsx-runtime');
const {render, fireEvent, screen, waitFor, cleanup, act} = req('@testing-library/react');
const {Popover, Switch} = req('radix-ui');
const calls = [];
let sid = 'session-real-42';
let guard = false;
let fail = false;
let accepted = true;
const values = {favorites:['openai::gpt-test','copilot::copilot-test']};
const host = {
 models:{select:async(selection)=>{
   calls.push({method:'native.select',selection,sid});
   if(fail) throw new Error('test gateway unavailable');
   return accepted;
 }},
 state:{focusedSessionId:{get:()=>sid}, model:{get:()=> 'gpt-test'}},
 request:async(method,params)=>{
  calls.push({method,params});
  if(method==='model.options') return {model:'gpt-test',provider:'openai',providers:[{slug:'openai',name:'OpenAI',authenticated:true,models:['gpt-test','mini-test']},{slug:'anthropic',name:'Anthropic',authenticated:true,models:['claude-test']},...(!params.explicit_only || params.include_unconfigured ? [{slug:'copilot',name:'GitHub Copilot',authenticated:false,models:['copilot-test']}] : [])]};
  if(fail) throw new Error('test gateway unavailable');
  return guard && !params.confirm_expensive_model ? {confirm_required:true,confirm_message:'Подтверди'} : {value:'ok'};
 },
 notifyError:message=>calls.push({error:message})
};
const sdk = {
 Button:React.forwardRef(({variant, ...props},ref)=>runtime.jsx('button',{...props,ref})),
 Codicon:({name})=>runtime.jsx('i',{'data-icon':name}),
 Switch:props=>runtime.jsx(Switch.Root,{...props,children:runtime.jsx(Switch.Thumb,{})}),
 Popover:Popover.Root, PopoverTrigger:Popover.Trigger,
 PopoverContent:props=>runtime.jsx(Popover.Portal,{children:runtime.jsx(Popover.Content,{...props})}),
 SearchField:({onChange,containerClassName,inputClassName,loading,variant,...props})=>runtime.jsx('input',{...props,onChange:e=>onChange(e.target.value)}),
 Separator:()=>runtime.jsx('hr',{}),
 cn:(...args)=>args.filter(Boolean).join(' '),
 useValue:atom=>atom.get(), host,
 surfaceModelSwitchConfirm:async opts=>{calls.push({confirm:opts.model});const result=await opts.requestConfirmed();opts.finish?.(result);return true;}
};
async function main(){
 const file = process.argv[2];
 const source=fs.readFileSync(file,'utf8');
 const transformed=source.replace(/import\s*\{([\s\S]*?)\}\s*from\s*['"](@hermes\/plugin-sdk|react\/jsx-runtime|react)['"]/g,(_,members,name)=>`const {${members}} = modules[${JSON.stringify(name)}];`).replace('export default','return');
 const plugin = new Function('modules',transformed)({'@hermes/plugin-sdk':sdk,'react':React,'react/jsx-runtime':runtime});
 let contribution;
 plugin.register({storage:{get:(k,f)=>values[k]??f,set:(k,v)=>values[k]=v},register:c=>contribution=c});
 assert.equal(contribution.area,'composer.actions');
 const Wrapper=()=>contribution.render();
 render(runtime.jsx(Wrapper,{}));
 assert.equal(screen.getByTestId('favorites-models-button').textContent,'');
 await new Promise(r=>setTimeout(r,20));
 await act(async()=>{ fireEvent.click(screen.getByTestId('favorites-models-button'));});
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Вернуться в чат'})),{timeout:800});
 console.log('PASS: actual Radix trigger opens controlled popover');
 if(process.argv.includes('--open-only')){cleanup();return;}
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Выбрать gpt-test'})));
 assert.equal(screen.getByRole('switch',{name:'Установленные провайдеры'}).getAttribute('aria-checked'),'false');
 assert.equal(screen.queryByRole('textbox',{name:'Поиск модели'}),null);
 assert.equal(screen.queryByRole('button',{name:'Провайдер OpenAI'}),null);
 console.log('PASS: catalog hidden by default, favorites still visible');
 await act(async()=>{ fireEvent.click(screen.getByRole('switch',{name:'Установленные провайдеры'}));});
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Провайдер OpenAI'})));
 assert.equal(values.showProviders,true);
 assert.equal(screen.queryByRole('button',{name:'Провайдер GitHub Copilot'}),null);
 assert.equal(screen.queryByRole('button',{name:'Выбрать copilot-test'}),null);
 assert.ok(values.favorites.includes('copilot::copilot-test'));
 const reads=calls.filter(c=>c.method==='model.options');
 assert.ok(reads.every(c=>c.params.explicit_only===true && c.params.include_unconfigured===false));
 console.log('PASS: configured-only API source and favorites restricted to its models; saved unavailable favorites preserved');
 const provider=()=>screen.getByRole('button',{name:'Провайдер OpenAI'});
 assert.equal(provider().getAttribute('aria-expanded'),'false');
 assert.equal(screen.queryByRole('button',{name:'Модель mini-test'}),null);
 await act(async()=>{ fireEvent.click(provider());});
 assert.equal(provider().getAttribute('aria-expanded'),'true');
 assert.ok(screen.queryByRole('button',{name:'Модель mini-test'}));
 await act(async()=>{ fireEvent.click(provider());});
 assert.equal(provider().getAttribute('aria-expanded'),'false');
 assert.equal(screen.queryByRole('button',{name:'Модель mini-test'}),null);
 assert.equal(values.collapsedProviders.openai,true);
 await act(async()=>{ fireEvent.click(provider());});
 assert.equal(values.collapsedProviders.openai,false);
 console.log('PASS: independent provider collapse/expand persists');
 await act(async()=>{ fireEvent.click(screen.getByRole('switch',{name:'Установленные провайдеры'}));});
 assert.equal(screen.queryByRole('button',{name:'Провайдер OpenAI'}),null);
 assert.ok(screen.queryByRole('button',{name:'Выбрать gpt-test'}));
 assert.equal(values.showProviders,false);
 await act(async()=>{ fireEvent.click(screen.getByRole('switch',{name:'Установленные провайдеры'}));});
 assert.equal(provider().getAttribute('aria-expanded'),'true');
 console.log('PASS: hide/show catalog preserves favorites and group state');
 await act(async()=>{ fireEvent.change(screen.getByRole('textbox',{name:'Поиск модели'}),{target:{value:'mini-test'}});});
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Добавить в избранное mini-test'})));
 assert.equal(screen.queryByRole('button',{name:'Добавить в избранное claude-test'}),null);
 await act(async()=>{ fireEvent.click(screen.getByRole('button',{name:'Добавить в избранное mini-test'}));});
 await waitFor(()=>assert.ok(values.favorites.includes('openai::mini-test')));
 console.log('PASS: search string + favorite persistence + immediate repaint');
 await act(async()=>{ fireEvent.click(screen.getByRole('button',{name:'Выбрать mini-test'}));});
 await waitFor(()=>assert.ok(calls.find(c=>c.method==='native.select')));
 const sw=calls.find(c=>c.method==='native.select');
 assert.deepEqual(sw.selection,{model:'mini-test',provider:'openai'});
 assert.equal(sw.sid,'session-real-42');
 await waitFor(()=>assert.equal(screen.queryByRole('button',{name:'Вернуться в чат'}),null));
 assert.equal(calls.filter(c=>c.method==='config.set').length,0);
 console.log('PASS: live selection delegates to native bridge, closes on success');
 await new Promise(resolve=>setTimeout(resolve,50));
 sid=null;
 await act(async()=>{ fireEvent.click(screen.getByTestId('favorites-models-button'));});
 await new Promise(resolve=>setTimeout(resolve,20));
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Выбрать mini-test'})));
 await act(async()=>{ fireEvent.click(screen.getByRole('button',{name:'Выбрать mini-test'}));});
 await waitFor(()=>assert.equal(screen.queryByRole('button',{name:'Вернуться в чат'}),null));
 assert.equal(calls.filter(c=>c.method==='native.select').at(-1).sid,null);
 assert.equal(calls.filter(c=>c.method==='config.set').length,0);
 assert.equal(calls.filter(c=>c.error).length,0);
 console.log('PASS: draft selects through bridge without global config or old blocking toast');
 await act(async()=>{ fireEvent.click(screen.getByTestId('favorites-models-button'));});
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Выбрать mini-test'})));
 sid='session-real-42';fail=true;
 await act(async()=>{ fireEvent.click(screen.getByRole('button',{name:'Выбрать mini-test'}));});
 await waitFor(()=>assert.ok(calls.find(c=>c.error?.includes('test gateway unavailable'))));
 console.log('PASS: gateway error shown, panel stays open');
 fail=false;
 await act(async()=>{ fireEvent.click(screen.getAllByRole('button',{name:'Убрать из избранного mini-test'})[0]);});
 await waitFor(()=>assert.ok(!values.favorites.includes('openai::mini-test')));
 console.log('PASS: remove persists and updates grid');
 await act(async()=>{ fireEvent.click(screen.getByRole('button',{name:'Вернуться в чат'}));});
 await waitFor(()=>assert.equal(screen.queryByRole('button',{name:'Вернуться в чат'}),null));
 await act(async()=>{ fireEvent.click(screen.getByTestId('favorites-models-button'));});
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Вернуться в чат'})));
 console.log('PASS: close and reopen retains catalog');
 assert.equal(screen.getByRole('switch',{name:'Установленные провайдеры'}).getAttribute('aria-checked'),'true');
 assert.equal(screen.getByRole('button',{name:'Провайдер OpenAI'}).getAttribute('aria-expanded'),'true');
 cleanup();
 render(runtime.jsx(Wrapper,{}));
 await act(async()=>{ fireEvent.click(screen.getByTestId('favorites-models-button'));});
 await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Провайдер OpenAI'})));
 assert.equal(screen.getByRole('switch',{name:'Установленные провайдеры'}).getAttribute('aria-checked'),'true');
 assert.equal(screen.getByRole('button',{name:'Провайдер OpenAI'}).getAttribute('aria-expanded'),'true');
 console.log('PASS: settings restored after component remount');
 cleanup();
}
main().then(()=>process.exit(0)).catch(err=>{console.error(err.message);process.exit(1)});

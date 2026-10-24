import json, sys
a, b, start = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
comp = json.load(open('comp.json'))[a:b]
tpl = open('render_tpl.js').read()
code = tpl.replace('__DATA__', json.dumps(comp, separators=(',', ':'), ensure_ascii=False)).replace('__START__', str(start))
open(f'code_{a}_{b}.js', 'w').write(code)
print(len(code))

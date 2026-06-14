import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find settings IIFE click handler
idx = c.find("addEventListener('click'")
if idx < 0:
    idx = c.find('addEventListener("click"')

# Find the function body
fn_start = c.find('function', idx)
fn_end = c.find('});', fn_start)
if fn_end > 0:
    fn_end += 2
code = c[idx:fn_end]
print(code[:1500])
print("\n\n=== END OF HANDLER ===")

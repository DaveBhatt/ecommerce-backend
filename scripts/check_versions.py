import importlib
import importlib.metadata as md

for name in ("bcrypt","passlib"):
    try:
        m = importlib.import_module(name)
        print(f"{name}: file={getattr(m,'__file__',None)}")
        print(f"{name}: __version__={getattr(m,'__version__',None)}")
        print(f"{name}: __about__={getattr(m,'__about__',None)}")
    except Exception as e:
        print(f"{name}: import error: {e}")

# distributions
for dist in md.distributions():
    name = dist.metadata.get('Name','')
    if name.lower() in ('bcrypt','passlib'):
        print('dist:', name, dist.version)

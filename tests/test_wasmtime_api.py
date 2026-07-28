"""Quick check of wasmtime Instance.exports API."""

from wasmtime import Instance, Module, Store


def main():
    s = Store()
    wat = r'(module (func (export "add") (param i32 i32) (result i32) (i32.add (local.get 0) (local.get 1))))'
    mod = Module(s.engine, wat)
    inst = Instance(s, mod, [])
    ex = inst.exports(s)
    names = list(ex)
    print("names", names)
    print("has items", hasattr(ex, "items"))
    if names:
        print("first kind", type(ex[names[0]]).__name__)
    add_fn = ex["add"]
    out = add_fn(s, 1, 2)
    print("add(1,2)", out)


if __name__ == "__main__":
    main()

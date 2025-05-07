# Example usage of qnngds

For each new project, set up a `pdk` directory
```text
example/
  main.py               main function, generate your layout
  pdk/
    __init__.py         export symbols
    layer_map.py        define GDS layers
    cross_section.py    define CrossSections for routing
    components.py       define any custom devices/circuits
    pdk.py              define PDK from cross_section, components, and layer_map
```

`layer_map` (and `cross_section` to some extent) will probably be mostly boilerplate. We could create a template github repository that already includes a skeleton so users just need to write `main.py` and tweak the PDK to their needs.

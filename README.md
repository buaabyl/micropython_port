# Micropython Porting

可能最好的还是先用PicoC吧，这个方便一点。而Micropython的各种东西不太熟悉，需要花时间看看。


## 添加自定义的模块

在 windows/mpconfigport.h 里有自定义模块的添加

```
extern const struct _mp_obj_module_t mp_module_os;
extern const struct _mp_obj_module_t mp_module_time;
#define MICROPY_PORT_BUILTIN_MODULES \
    { MP_OBJ_NEW_QSTR(MP_QSTR_utime), (mp_obj_t)&mp_module_time }, \
    { MP_OBJ_NEW_QSTR(MP_QSTR_umachine), (mp_obj_t)&mp_module_machine }, \
    { MP_OBJ_NEW_QSTR(MP_QSTR_uos), (mp_obj_t)&mp_module_os }, \
```

然后在 py/objdmoule.c 里

```
STATIC const mp_rom_map_elem_t mp_builtin_module_table[] = {

......

#if MICROPY_PY_BTREE
    { MP_ROM_QSTR(MP_QSTR_btree), MP_ROM_PTR(&mp_module_btree) },
#endif

    // extra builtin modules as defined by a port
    MICROPY_PORT_BUILTIN_MODULES
};
```



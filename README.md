# Micropython Porting

可能最好的还是先用PicoC吧，这个方便一点。而Micropython的各种东西不太熟悉，需要花时间看看。


## build

Micropython使用2步编译，这样的好处是已知的字符串都是rodata，不需要占用ram空间。
1. 预处理所有的C文件，然后用Python脚本找到所有的QSTR，生成一个数组。
2. 将上边的数组生成一个头文件，然后正常的编译。

调用的地方

```
./py/modsys.c:38:   #include "genhdr/mpversion.h"
./unix/main.c:50:   #include "genhdr/mpversion.h"
./py/qstr.c:106:    #include "genhdr/qstrdefs.generated.h"
./py/qstr.h:42:     #include "genhdr/qstrdefs.generated.h"
```

其实只需要2个头文件：

1. mpversion.h
2. qstrdefs.generated.h



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



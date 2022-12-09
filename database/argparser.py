class ArgParser:
    def __parse_args(self, target, store, default, Key, **args):
        if isinstance(default, list):
            value = default.copy()
        else:
            value = default
        for arg in args:
            key = arg.lower()
            if isinstance(default, list):
                if key == Key + 's':
                    value.extend(args[arg])
                elif key == Key:
                    value.append(args[arg])
            else:
                if key == Key:
                    value = args[arg]
        setattr(target, store, value)        

    def parse_args(self, flags, target, flag_map, **args):
        for map in flag_map:
            if map["flag"] in flags:
                self.__parse_args(target, map["attribute"], map["default"], map["key"], **args)
    


from .types import Number, Pointer, sizeof, types_py


class Scope(object):
    """ A scope (block/function) with its address table """
    def __init__(self, scope_name, parent_scope=None):
        self.scope_name = scope_name
        # Parent_scope is None if this is a global scope or a function scope (top of the frame)
        self.parent_scope = parent_scope
        self._addresses = dict()

    def __setitem__(self, key, value):
        self._addresses[key] = value

    def __getitem__(self, item):
        return self._addresses[item]

    def __contains__(self, key):
        return key in self._addresses

    def __repr__(self):
        lines = [
            '{}:{}'.format(key, val) for key, val in self._addresses.items()
        ]
        title = '{}\n'.format(self.scope_name)
        return title + '\n'.join(lines)


class Frame(object):
    """ A single stack frame, contains nested scopes """
    def __init__(self, frame_name):
        self.frame_name = frame_name
        # depth = 00
        self.curr_scope = Scope(
            '{}.scope_00'.format(frame_name),
            None
        )

    def new_scope(self):
        # increase depth
        self.curr_scope = Scope(
            '{}{:02d}'.format(
                self.curr_scope.scope_name[:-2],
                int(self.curr_scope.scope_name[-2:]) + 1
            ),
            self.curr_scope
        )

    def del_scope(self):
        self.curr_scope = self.curr_scope.parent_scope

    def find_key(self, key):
        scope = self.curr_scope
        while scope and key not in scope:
            scope = scope.parent_scope
        return scope

    def _get_scopes(self):
        scopes = []
        curr_scope = self.curr_scope
        while curr_scope is not None:
            scopes.append(curr_scope)
            curr_scope = curr_scope.parent_scope
        return scopes

    def __contains__(self, key):
        return key in self._get_scopes()

    def __repr__(self):
        lines = [
            '{}\n{}'.format(
                scope,
                '-' * 40
            ) for scope in self._get_scopes()
        ]

        title = 'Frame: {}\n{}\n'.format(
            self.frame_name,
            '*' * 40
        )

        return title + '\n'.join(lines)


class Stack(object):
    """ A stack, contains stacked frames """
    def __init__(self):
        # curr_frame is always the last in the list
        self.curr_frame = None
        self.frames = []

    def is_empty(self):
        return self.curr_frame is None

    def new_frame(self, frame_name):
        self.frames.append(Frame(frame_name))
        self.curr_frame = self.frames[-1]

    def del_frame(self):
        self.frames.pop(-1)
        if len(self.frames) == 0:
            self.curr_frame = None
        else:
            self.curr_frame = self.frames[-1]

    def __repr__(self):
        lines = [
            '{}'.format(frame) for frame in self.frames
        ]
        return '\n'.join(lines)


class Memory(object):
    """
        A simulated program memory, contains a raw_memory map that maps addresses to values and a stack with frames.
        Every frame contains nested scopes and each scope maps symbol names to addresses. There is also a global scope.

        Mapping name->address in scopes and address->val in raw_memory is a way to simulate C memory system in python.
        In reality the raw_memory map would not be necessary since scope members would inherently have addresses.
    """

    # Addresses start from this number and always grow
    STARTING_ADDRESS = int(1e6)

    def __init__(self):
        self.global_scope = Scope('global_scope')
        self.stack = Stack()
        self.raw_memory = dict()
        self.next_free_address = Memory.STARTING_ADDRESS

    def malloc(self, block_sz):
        """ Allocates a memory block """
        ret_address = self.next_free_address
        self.next_free_address += block_sz
        return ret_address

    def declare(self, var_type, var_name):
        """ Reserves space for a variable """

        # find the current scope
        if self.stack.is_empty():
            scope = self.global_scope
        else:
            scope = self.stack.curr_frame.curr_scope

        # name -> address
        scope[var_name] = self.malloc(sizeof(var_type))

        # address -> value
        if var_type[-1] == '*':
            self.raw_memory[scope[var_name]] = Pointer(var_type)
        elif var_type in types_py:
            self.raw_memory[scope[var_name]] = Number(var_type)
        else:
            self.raw_memory[scope[var_name]] = None

    def find_key(self, key):
        """ Returns the scope with the given key starting from the current scope """
        if self.stack.is_empty():
            return self.global_scope
        # Look in the current frame
        scope = self.stack.curr_frame.find_key(key)
        if scope is not None:
            return scope
        # If nothing try in the global scope
        if key in self.global_scope:
            return self.global_scope
        # Semantic analysis should ensure the key exists, this should never happen
        raise RuntimeError("Failed to find {} in the current scope".format(key))

    def get_address(self, key):
        scope = self.find_key(key)
        return scope[key]

    def set_at_address(self, address, value):
        self.raw_memory[address] = value

    def get_at_address(self, address):
        if address not in self.raw_memory:
            # Return a random number
            self.raw_memory[address] = Number('int')
        return self.raw_memory[address]

    def __setitem__(self, key, value):
        address = self.get_address(key)
        self.set_at_address(address, value)

    def __getitem__(self, key):
        address = self.get_address(key)
        return self.get_at_address(address)

    def new_frame(self, frame_name):
        self.stack.new_frame(frame_name)

    def del_frame(self):
        self.stack.del_frame()

    def new_scope(self):
        self.stack.curr_frame.new_scope()

    def del_scope(self):
        self.stack.curr_frame.del_scope()

    def __repr__(self):
        return "{}\nStack\n{}\n{}".format(
            self.global_scope,
            '=' * 40,
            self.stack
        )

    def __str__(self):
        return self.__repr__()



from base import Action
from io import TextIOWrapper
from typing import Iterable, List, Set, Dict
from collections import deque

""" ======================================== Blocksworld base ======================================== """


class Block(object):
    def __init__(self, label: str):
        """
        Default constructor of a Block
        :param label:  the char label of the Block
        """
        self.label = label

    def __hash__(self):
        return hash(self.label)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.label == other.label
        else:
            return False

    def __str__(self):
        return self.label

    def __repr__(self):
        return self.__str__()


class Station(Block):
    def __init__(self, label: str):
        super(Station, self).__init__(label)

    def __str__(self):
        return "#" + self.label

    def __repr__(self):
        return self.__str__()


""" ======================================== Blocksworld actions ======================================== """


class BlocksWorldAction(Action):

    def __init__(self, type: str, **kwargs):
        self._type = type
        self._args = []

        if 'arg1' in kwargs:
            self._args.append(kwargs['arg1'])

        if 'arg2' in kwargs:
            if not 'arg1' in kwargs:
                raise ValueError("Cannot construct a BlocksWorld action which has no first argument!")

            else:
                self._args.append(kwargs['arg2'])

    def has_no_args(self) -> bool:
        return not self._args

    def has_one_arg(self) -> bool:
        return len(self._args) == 1

    def has_two_args(self) -> bool:
        return len(self._args) == 2

    def get_first_arg(self) -> Block:
        if len(self._args) >= 1:
            return self._args[0]

        raise ValueError("Action %s has no first argument!" % self._type)

    def get_second_arg(self) -> Block:
        if len(self._args) == 2:
            return self._args[1]

        raise ValueError("Action %s has no second argument!" % self._type)

    def get_argument(self) -> Block:
        if self.has_one_arg():
            return self.get_first_arg()

        raise ValueError("Action %s has either no argument, or two arguments" % self._type)

    def get_type(self) -> str:
        return self._type

    def __hash__(self):
        if self.has_one_arg():
            return 42
        else:
            return sum([hash(arg) for arg in self._args])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._type != other._type:
                return False

            elif len(self._args) != len(other._args):
                return False

            elif not all(map(lambda tpl: tpl[0] == tpl[1], zip(self._args, other._args))):
                return False

            else:
                return True

        return False

    def __str__(self):
        if self.has_no_args():
            return self._type

        return self._type + "(" + " ".join([str(b) for b in self._args]) + ")"


class PickUp(BlocksWorldAction):
    def __init__(self, block: Block):
        super(PickUp, self).__init__("pickup", arg1=block)


class PutDown(BlocksWorldAction):
    def __init__(self, block: Block):
        super(PutDown, self).__init__("putdown", arg1=block)


class Unstack(BlocksWorldAction):
    def __init__(self, target_block: Block, from_block: Block):
        super(Unstack, self).__init__("unstack", arg1=target_block, arg2=from_block)


class Stack(BlocksWorldAction):
    def __init__(self, target_block: Block, on_block: Block):
        super(Stack, self).__init__("stack", arg1=target_block, arg2=on_block)


class Lock(BlocksWorldAction):
    def __init__(self, block: Block):
        super(Lock, self).__init__("lock", arg1=block)


class AgentCompleted(BlocksWorldAction):
    def __init__(self):
        super(AgentCompleted, self).__init__("agent_completed")


class NoAction(BlocksWorldAction):
    def __init__(self):
        super(NoAction, self).__init__("no_action")


""" ======================================== Blocksworld state ======================================== """


class Predicate(object):

    def __init__(self, type: str, **kwargs: Dict[str, Block]):
        self.type = type
        self.first_arg = None
        self.second_arg = None
        self._args = []

        self.nr_arguments = 0

        if "arg1" in kwargs:
            self.first_arg = kwargs["arg1"]
            self._args.append(self.first_arg)
            self.nr_arguments += 1

        if "arg2" in kwargs:
            self.second_arg = kwargs["arg2"]
            self._args.append(self.second_arg)
            self.nr_arguments += 1

    def get_type(self) -> str:
        return self.type

    def get_first_arg(self) -> Block:
        if self.first_arg:
            return self.first_arg

        raise ValueError("Predicate %s has no arguments" % self.type)

    def get_second_arg(self) -> Block:
        if self.second_arg:
            return self.second_arg

        raise ValueError("Predicate %s has less than two arguments" % self.type)

    def get_argument(self) -> Block:
        if self.nr_arguments >= 1:
            return self.get_first_arg()

        raise ValueError("Predicate %s has no arguments" % self.type)

    def __str__(self):
        if self.nr_arguments == 0:
            return self.type

        return self.type + "(" + " ".join([str(b) for b in self._args]) + ")"

    def __repr__(self):
        return self.__str__()


class ArmEmpty(Predicate):
    def __init__(self):
        super(ArmEmpty, self).__init__("arm_empty")


class Hold(Predicate):
    def __init__(self, block: Block):
        super(Hold, self).__init__("hold", arg1=block)


class On(Predicate):
    def __init__(self, top_block: Block, bottom_block: Block):
        super(On, self).__init__("on", arg1=top_block, arg2=bottom_block)


class OnTable(Predicate):
    def __init__(self, block: Block):
        super(OnTable, self).__init__("on_table", arg1=block)


class Clear(Predicate):
    def __init__(self, block: Block):
        super(Clear, self).__init__("clear", arg1=block)


""" ======================================== Blocksworld state ======================================== """


class BlockStack(object):
    """
    Class representing a stack of blocks in blocksworld.
    The state of the stack can be accessed as a list of predicates `getPredicates()' or directly using the
    properties of the stack, using `getBlocks()', `contains(Block)', `isOn(Block, Block)' and
    `isClear(Block)'.
    For methods working on a group of `Stacks', see `BlocksWorld' class.
    """

    def __init__(self, base: Block = None, blocks: Iterable = None, locked: Iterable = None):
        if not base and not blocks:
            raise ValueError("Cannot initialize a stack without any block!")

        if blocks:
            self.blocks = deque(list(blocks))

        elif base:
            self.blocks = deque([base])

        if locked:
            self.locked_blocks = list(locked)
        else:
            self.locked_blocks = []

    def sane(self) -> bool:
        if not self.blocks and not self.locked_blocks:
            raise ValueError("This stack contains no blocks")

    def is_single_block(self) -> bool:
        return len(self.get_blocks()) == 1

    def is_on_table(self, block: Block) -> bool:
        self.sane()
        if self.get_blocks()[0] == block:
            return True

        return False

    def is_clear(self, block: Block) -> bool:
        self.sane()
        if self.blocks[-1] == block:
            return True

        return False

    def is_on(self, top_block: Block, bottom_block: Block):
        self.sane()
        if not top_block in self.get_blocks():
            raise ValueError("This stack does not contain block %s" % str(top_block))

        if not bottom_block in self.get_blocks():
            raise ValueError("This stack does not contain block %s" % str(bottom_block))

        bottom_block_idx = self.get_blocks().index(bottom_block)
        if self.get_blocks()[bottom_block_idx + 1] == top_block:
            return True

        return False

    def get_above(self, block: Block) -> Block:
        if not block in self.get_blocks():
            raise ValueError("Block [%s] is not in this stack" % str(block))

        if len(self.get_blocks()) == 1:
            return None
        else:
            block_idx = self.get_blocks().index(block)
            return self.get_blocks()[block_idx + 1]

    def get_below(self, block: Block) -> Block:
        if not block in self.get_blocks():
            raise ValueError("Block [%s] is not in this stack" % str(block))

        if self.is_on_table(block):
            return None
        else:
            block_idx = self.get_blocks().index(block)
            return self.get_blocks()[block_idx - 1]

    def get_blocks(self) -> List[Block]:
        """
        Get all blocks in this stack as a list
        :return the list of all blocks
        """
        from copy import copy
        ret = copy(self.get_locked_blocks())
        ret.extend(list(copy(self.blocks)))
        return ret

    def get_locked_blocks(self) -> List[Block]:
        from copy import copy
        return copy(self.locked_blocks)

    def get_top_block(self) -> Block:
        if self.get_blocks():
            return self.get_blocks()[-1]
        return None

    def get_bottom_block(self) -> Block:
        if self.get_blocks():
            return self.get_blocks()[0]
        return None

    def is_locked(self, block: Block) -> bool:
        if block in self.locked_blocks:
            return True
        return False

    def unstack(self, to_unstack: Block, unstack_from: Block) -> Block:
        """
        Unstacks the topmost block of this stack.
        :param toUnstack: the block to unstack from the tower (or a `Block' instance with the same label).
        :param unstackFrom: the block that is under it (or a `link Block' instance with the same label).
        :return: the block that was unstacked (the actual instance in this stack).
        :raises ValueError if the block cannot be unstacked from this stack or if the stack is not sane
        """
        self.sane()

        if not self.get_blocks():
            raise ValueError("All blocks in this stack are locked.")

        if self.get_blocks() and self.get_blocks()[-1] == to_unstack:
            if self.is_single_block():
                raise ValueError("Block [%s] is directly on the table. Use pickup." % str(to_unstack))

            if not self.get_blocks()[-2] == unstack_from:
                raise ValueError("Block [%s] is not over [%s]." % (str(to_unstack), str(unstack_from)))

            return self.blocks.pop()

        raise ValueError("Block [%s] is not the topmost block of this stack" % str(to_unstack))

    def stack(self, to_stack: Block, stack_over: Block) -> None:
        self.sane()
        if self.get_blocks()[-1] == stack_over:
            self.blocks.append(to_stack)
        else:
            raise ValueError("Block [%s] is not the topmost block of this stack" % str(stack_over))

    def lock(self, block: Block) -> None:
        """
        :param block: block to lock. Locked blocks can never be moved again
        """
        self.sane()
        if block in self.locked_blocks:
            raise ValueError("Block [%s] is already locked" % str(block))

        if not self.is_on_table(block) and not self.get_below(block) in self.locked_blocks:
            raise ValueError("The block under [%s] is not locked" % str(block))

        # self.locked_blocks.insert(0, block)
        self.locked_blocks.append(block)
        self.blocks.popleft()

    def __contains__(self, item):
        if not isinstance(item, Block):
            return False
        else:
            ret = True if item in self.get_blocks() else False
            return ret

    def __hash__(self):
        if not self.get_blocks():
            return 42

        return sum([hash(block) for block in list(self.get_blocks())])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            this_block_list = list(self.get_blocks())
            other_block_list = list(other.get_blocks())

            if len(this_block_list) != len(other_block_list):
                return False

            for i in range(len(this_block_list)):
                if this_block_list[i] != other_block_list[i]:
                    return False

            return True

        else:
            return False

    def __str__(self):
        return " ".join([str(b) for b in list(self.get_blocks())])

    def __repr__(self):
        return self.__str__()

    def get_predicates(self) -> List[Predicate]:
        above = None

        ret = []
        for b in reversed(self.get_blocks()):
            if not above:
                ret.append(Clear(b))

            else:
                ret.append(On(above, b))

            above = b

        ret.append(OnTable(above))

        return ret


class BlocksWorld(object):
    def __init__(self, input_stream: TextIOWrapper = None):
        self.stacks = []
        self.all_blocks = set([])

        if input_stream:
            self.__read_world(input_stream)

    def __read_world(self, input_stream: TextIOWrapper):
        self.stacks = []
        ts = {}

        lines = input_stream.readlines()

        for iLevel in range(len(lines)):
            line = lines[iLevel].strip()
            if len(line) == 0:
                if iLevel > 0:
                    break
                continue

            for char_idx in range(len(line)):
                if line[char_idx] != ' ' and line[char_idx] != '.':
                    b = Block(str(line[char_idx]))
                    if b in self.all_blocks:
                        raise IOError("duplicate blocks not allowed in input file")

                    if char_idx in ts:
                        if not (iLevel - 1) in ts[char_idx]:
                            raise IOError("space found in tower")

                        ts[char_idx][iLevel] = b
                    else:
                        ts[char_idx] = {
                            iLevel: b
                        }

        for stack_map in ts.values():
            if not (len(lines) - 1) in stack_map:
                raise IOError("tower does not reach the table")

            tower = []
            for i in range(len(lines)):
                if i in stack_map:
                    b = stack_map[i]
                    tower.insert(0, b)
                    if b in self.all_blocks:
                        raise ValueError("duplicate block found")
                    else:
                        self.all_blocks.add(b)

            self.stacks.append(BlockStack(blocks=tower))

    def get_all_blocks(self) -> Set[Block]:
        return set(list(self.all_blocks))

    def exists(self, block: Block) -> bool:
        return block in self.all_blocks

    def get_stack(self, block: Block) -> BlockStack:
        """
        Gets the stack containing a given block
        :param block: the block to search for
        :return: The `BlockStack' containing the block
        """
        if not block in self.all_blocks:
            raise ValueError("Block [%s] has never existed in this world\n %s" % (str(block), str(self)))

        for stack in self.stacks:
            if block in stack.get_blocks():
                return stack

        raise ValueError("Block [%s] is not currently in any stack" % str(block))

    def get_stacks(self) -> List[BlockStack]:
        from copy import copy
        return copy(self.stacks)

    def pick_up(self, block: Block):
        stack = self.get_stack(block)

        if not stack.is_single_block():
            raise ValueError("Block [%s] is not in a single-block stack. Use unstack instead " % str(block))

        self.stacks.remove(stack)

        return stack.get_top_block()

    def put_down(self, block: Block, current_stack: BlockStack) -> BlockStack:
        if not block in self.all_blocks:
            raise ValueError("Block [%s] has never existed in this world" % str(block))

        stack = BlockStack(base=block)
        stack_idx = self.stacks.index(current_stack)
        self.stacks.insert(stack_idx, stack)

        return stack

    def unstack(self, to_unstack: Block, unstack_from: Block) -> Block:
        return self.get_stack(to_unstack).unstack(to_unstack=to_unstack, unstack_from=unstack_from)

    def stack(self, to_stack: Block, stack_over: Block) -> None:
        self.get_stack(stack_over).stack(to_stack=to_stack, stack_over=stack_over)

    def lock(self, block: Block) -> None:
        self.get_stack(block).lock(block)

    def is_on_table(self, block: Block) -> bool:
        return self.get_stack(block).is_on_table(block)

    def clone(self) -> 'BlocksWorld':
        from copy import copy

        world = BlocksWorld()
        world.all_blocks = set(copy(self.get_all_blocks()))
        world.stacks = []

        for stack in self.stacks:
            world.stacks.append(BlockStack(blocks=stack.get_blocks(), locked=stack.get_locked_blocks()))

        return world

    def __str__(self):
        return self._print_world(0)

    def __repr__(self):
        return self.__str__()

    def _print_world(self, stack_space: int,
                     prefixes: Dict[BlockStack, List[str]] = None,
                     suffixes: Dict[BlockStack, List[str]] = None,
                     print_table=True) -> str:

        stack_space = max(stack_space, 3)
        max_height = max([len(s.get_blocks()) for s in self.stacks])

        ret = ""
        ret += self._print_additional(prefixes, stack_space)
        for y in range(max_height, 0, -1):
            ret += " "

            for stack in self.stacks:
                blocks = list(reversed(stack.get_blocks()))
                if len(blocks) >= y:
                    b = blocks[len(blocks) - y]
                    lck = True if b in stack.get_locked_blocks() else False

                    ret += "{" if lck else "["
                    ret += str(b)
                    ret += "}" if lck else "]"

                else:
                    ret += "   "

                for x in range(3, stack_space):
                    ret += " "

            ret += "\n"

        if print_table:
            ret += "=" * (len(self.stacks) * stack_space + 3)

        ret += self._print_additional(suffixes, stack_space)

        return ret

    def _print_additional(self, additional: Dict[BlockStack, List[str]], stack_space: int) -> str:
        ret = ""

        if not additional:
            return ""

        maxA = max([len(a) for a in additional.values()])

        for y in range(maxA):
            for stack in self.stacks:
                if stack in additional:
                    ret += additional[stack][y]
                    ret += " " * (stack_space - len(additional[stack][y]))
                else:
                    ret += " " * stack_space

            ret += "\n"

        return ret

    def to_predicates(self) -> Iterable:
        ret = []
        for stack in self.stacks:
            ret.extend(stack.get_predicates())

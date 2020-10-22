class PostprocessingPattern:

    def __init__(self, condition, success_value=True, condition_args=None):
        """A PostprocessingPattern defines a single condition to check against an entity.
        condition (function): A function to call on an entity. If the result of
            the function call equals success_value, then the pattern passes.
        success_value: The value which should be returned by condition(ent)
            in order for the pattern to pass. Default True.
        condition_args (function or None): Optional positional arguments to call
            with condition(ent, *condition_args). If None, will just call
            condition(ent). Default None.
        """
        self.condition = condition
        self.success_value = success_value
        self.condition_args = condition_args

    def __call__(self, ent):
        if self.condition_args is None:
            result = self.condition(ent)
        else:
            result = self.condition(ent, *self.condition_args)
        # print(result, self.success_value)
        return result == self.success_value
        # if result == self.success_value:
        #     return True
        # return False
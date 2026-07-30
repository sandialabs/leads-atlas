class VistaloaderError(Exception):
    """Root level error for errors in the `leads_atlas` library

    Without further context, this error is not recoverable.
    """

    pass


class PanicError(Exception):
    """Exception raised by panic(), todo(), unimplemented(), unreachable(), etc.

    Mimics Rust's panic system for marking unfinished or impossible code paths.
    """

    pass


def _panic_with_location(tag: str, msg: str | None = None):
    """Internal helper to raise a PanicError with location information."""
    import inspect

    frame = inspect.currentframe().f_back.f_back  # type: ignore
    filename = frame.f_code.co_filename  # type: ignore
    line_number = frame.f_lineno  # type: ignore

    if msg:
        error_msg = f"{tag}: {msg}\n    at {filename}:{line_number}"
    else:
        error_msg = f"{tag}\n    at {filename}:{line_number}"

    raise PanicError(error_msg)


def todo(msg: str | None = None):
    """Marks code as needing to be done yet. Immediately raises an error with the provided message.

    Mimics Rust's todo!() macro. Use this as a placeholder while prototyping or
    sketching out functionality that you plan to implement later.

    Args:
        msg (str | None): Context behind the to-do message

    Raises:
        PanicError: Raised to share the provided to-do message with location info
    """
    _panic_with_location("not yet implemented", msg)


def unimplemented(msg: str | None = None):
    """Marks code as unimplemented. Immediately raises an error with the provided message.

    Mimics Rust's unimplemented!() macro. Use this for functionality that you have
    no intention of implementing (e.g., stub methods required by an interface but
    not needed in your specific use case).

    Args:
        msg (str | None): Context behind why this is unimplemented

    Raises:
        PanicError: Raised to share the provided message with location info
    """
    _panic_with_location("not implemented", msg)


def unreachable(msg: str | None = None):
    """Marks code as unreachable. Immediately raises an error if executed.

    Mimics Rust's unreachable!() macro. Use this for code paths that should
    logically never be reached based on your program's invariants. If this
    executes, it indicates a bug in your code logic.

    Args:
        msg (str | None): Context behind why this is unreachable

    Raises:
        PanicError: Raised to share the provided message with location info
    """
    if msg:
        _panic_with_location("internal error: entered unreachable code", msg)
    else:
        _panic_with_location("internal error: entered unreachable code", None)


def panic(msg: str | None = None):
    """Immediately raises an error with the provided message.

    Mimics Rust's panic!() macro. Use this for unrecoverable errors where
    continuing execution would be unsafe or incorrect. This is for situations
    where an invariant has been violated or an assumption has been broken.

    Args:
        msg (str | None): Panic message

    Raises:
        PanicError: Raised to share the provided message with location info
    """
    if msg:
        _panic_with_location(msg, None)
    else:
        _panic_with_location("explicit panic", None)

# C++: a function template

This C++20 function accepts any contiguous sequence that can form a span. It
returns an optional value because an empty sequence has no first element.

```cpp
#include <optional>
#include <span>
#include <vector>

template<class T>
std::optional<T> first(std::span<const T> values)
{
    if (values.empty())
        return std::nullopt;
    return values.front();
}

int main()
{
    const std::vector<int> values{4, 8, 15};
    const auto value = first<int>(values);
    return value && *value == 4 ? 0 : 1;
}
```

Build with `clang++ -std=c++20 -Wall -Wextra example.cpp`. The returned value is a
copy; the span borrows the vector's storage and must not outlive it.

Use **DOCS → C++ LIBRARY** and enter `std::span`, `std::optional`, or
`std::vector`. The installed stdman pages include signatures, overloads,
requirements and examples from their cppreference snapshot. Search within a page
with `/Example`, then `n` for the next match. These pages are a reference snapshot,
not a promise that the installed compiler implements every listed feature.

// Final Demo: Optimization + Safety Check

void main() {
    // 1. Constant Propagation (Should fold to 12)
    int x = (10 * 10 + 44) / 12;
    print(x);

    // 2. Loop Safety (Should NOT become infinite or constant-folded)
    int arr[5];
    int i = 0;
    while (i < 3) {
        arr[i] = i * 10;
        print(arr[i]); // Should print 0, 10, 20
        ++i;
    }

    // 3. Logic & Functions
    if (check(x)) {
        print(999);
    }
}

bool check(int val) {
    return val == 12;
}

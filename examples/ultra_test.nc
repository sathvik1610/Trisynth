// ULTRA TEST: Limits & Features
// 1. Recursive Backtracking (Subset Sum-ish)
// 2. Optimization Candidates (Strength Reduction)
// 3. Shadowing & Scopes
// 4. Complex Logic & Control Flow

const int TARGET = 12;
int data[10];

void main() {
    print(11111); // START

    // 1. Initialize with Strength Reduction opportunities
    // i * 4 should become i << 2
    for (int i = 0; i < 10; ++i) {
        data[i] = i * 4; 
    }
    
    // 2. Recursive Search (Hoisted)
    // defined below
    int found_idx = find_target(0, 0); 
    print(found_idx); 

    // 3. Shadowing "Stress"
    int x = 999;
    {
        int x = 111;
        // Optimization Trap: x is constant 111 here.
        // But outer x is 999.
        // x * 2 -> 222 (Folded?)
        print(x * 2); 
    }
    print(x); // Should stay 999

    // 4. Control Flow Madness (Break/Continue/Logic)
    int k = 0;
    while (true) {
        if (k >= 10) break;
        
        // Strength Reduction: k / 2 -> k >> 1
        int half = k / 2;
        
        if (half % 2 != 0) {
            k = k + 1;
            continue; // Skip odds
        }
        
        print(half); // Should print only even halves: 0, 2, 4...
        k = k + 1;
    }
    
    // 5. Optimization Chain verification
    // (80 / 8) * 4 -> 10 * 4 -> 40
    // Optimizer should see: RSHIFT 3, LSHIFT 2 -> Folded to 40
    int opt = (80 / 8) * 4;
    print(opt);
}

// Recursive function to find if any value == TARGET (12)
// Returns index or -1
int find_target(int idx, int depth) {
    if (idx >= 10) return -1; // Base case: Out of bounds
    
    // Logic: Short circuit
    // data[idx] is i*4 => 0, 4, 8, 12, 16...
    // 12 is at index 3.
    
    if (data[idx] == TARGET) {
        return idx;
    }
    
    // Recurse
    return find_target(idx + 1, depth + 1);
}

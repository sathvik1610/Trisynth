// Trisynth Compiler Feature Demo
// Covers: Hoisting, Constants, Arrays, Loops, Logic, Inc/Dec

const int LIMIT = 5; // Immutable Constant

void main() {
    print(8888); // Marker start
    
    int arr[5]; // Array Declaration

    // For Loop + Inc/Dec
    for (int i = 0; i < LIMIT; ++i) {
        arr[i] = i * 10;
    }

    // Function Hoisting (compute defined below)
    int result = compute(arr[2], arr[4]); 
    print(result); // Expected: 20 + 40 = 60

    // Logic + If/Else
    if (result > 50 && result < 100) {
        print(1); // True
    } else {
        print(0);
    }
    
    // While Loop + Decrement
    int count = 3;
    while (count > 0) {
        print(count);
        --count;
    }
}

// Hoisted Function
int compute(int a, int b) {
    return a + b;
}

void main() {
    int a = 10;
    
    // 1. Mul Power of 2 -> LSHIFT
    int b = a * 8; 
    print(b);

    // 2. Div Power of 2 -> RSHIFT
    int c = b / 4;
    print(c);

    // 3. Zero Mul -> MOV 0
    int d = c * 0;
    print(d);

    // 4. Identity -> MOV
    int e = a + 0;
    print(e);
}

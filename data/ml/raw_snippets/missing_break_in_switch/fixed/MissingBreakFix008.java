package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix008 {
    static int calculate(int a, int b, char operator) {
        int result = 0;
        switch (operator) {
            case '+':
                result = a + b;
                break;
            case '-':
                result = a - b;
                break;
            case '*':
                result = a * b;
                break;
            case '/':
                result = a / b;
                break;
        }
        return result;
    }
}

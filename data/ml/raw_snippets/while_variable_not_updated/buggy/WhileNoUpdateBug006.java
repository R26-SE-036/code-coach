package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug006 {
    static int countDigits(int number) {
        int digits = 0;
        while (number != 0) {
            digits++;
        }
        return digits;
    }
}

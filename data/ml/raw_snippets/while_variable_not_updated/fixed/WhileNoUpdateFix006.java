package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix006 {
    static int countDigits(int number) {
        int digits = 0;
        while (number != 0) {
            digits++;
            number /= 10;
        }
        return digits;
    }
}

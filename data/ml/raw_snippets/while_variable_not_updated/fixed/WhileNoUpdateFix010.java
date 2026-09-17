package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix010 {
    static int nextPowerOfTwo(int limit) {
        int power = 1;
        while (power < limit) {
            System.out.println(power);
            power *= 2;
        }
        return power;
    }
}

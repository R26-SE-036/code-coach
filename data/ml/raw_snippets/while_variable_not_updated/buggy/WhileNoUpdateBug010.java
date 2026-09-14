package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug010 {
    static int nextPowerOfTwo(int limit) {
        int power = 1;
        while (power < limit) {
            System.out.println(power);
        }
        return power;
    }
}

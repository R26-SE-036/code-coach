package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix019 {
    public static void main(String[] args) {
        int multiplier = 1;
        final int base = 7;
        while (multiplier <= 12) {
            System.out.println(base + " x " + multiplier + " = " + base * multiplier);
            multiplier++;
        }
    }
}

package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix021 {
    static int yearsToDouble(double principal, double rate) {
        double amount = principal;
        int years = 0;
        while (amount < principal * 2) {
            years++;
            amount = amount * (1 + rate);
        }
        return years;
    }
}

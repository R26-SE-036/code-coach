package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug021 {
    static int yearsToDouble(double principal, double rate) {
        double amount = principal;
        int years = 0;
        while (amount < principal * 2) {
            years++;
        }
        return years;
    }
}

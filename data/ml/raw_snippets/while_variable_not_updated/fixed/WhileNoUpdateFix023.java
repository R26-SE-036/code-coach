package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix023 {
    static int daysToSellOut(int stock, int dailySales) {
        int days = 0;
        while (stock > 0) {
            days++;
            stock -= dailySales;
            System.out.println("Day " + days);
        }
        return days;
    }
}

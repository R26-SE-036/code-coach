package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug023 {
    static int daysToSellOut(int stock, int dailySales) {
        int days = 0;
        while (stock > 0) {
            days++;
            System.out.println("Day " + days);
        }
        return days;
    }
}

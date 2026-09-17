package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug007 {
    static double shippingCost(int zone) {
        double cost = 0.0;
        switch (zone) {
            case 1:
                cost = 5.0;
                break;
            case 2:
                cost = 7.5;
                break;
            case 3:
                cost = 10.0;
            case 4:
                cost = 15.0;
                break;
            default:
                cost = 20.0;
        }
        return cost;
    }
}

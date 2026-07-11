public class GenCleanTailIndex021 {
    static int tail(int[] prices) {
        return prices[prices.length - 1];
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "new";
        }
        return label;
    }
}

public class GenArrayIndexFix007 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static void showLast(int[] prices) {
        System.out.println(prices[prices.length - 1]);
    }

    static int drain2(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }
}

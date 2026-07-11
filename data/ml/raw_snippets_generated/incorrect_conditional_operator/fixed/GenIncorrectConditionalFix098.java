public class GenIncorrectConditionalFix098 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static void announce(int level) {
        if (level == 10) {
            System.out.println("hit the target");
        }
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int sum4(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}

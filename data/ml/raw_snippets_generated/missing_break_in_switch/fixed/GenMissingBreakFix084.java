public class GenMissingBreakFix084 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "final";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "expired";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int sum1(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
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

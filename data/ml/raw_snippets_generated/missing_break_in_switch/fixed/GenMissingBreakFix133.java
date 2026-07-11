public class GenMissingBreakFix133 {
    static int sum1(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain3(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "new";
                break;
            case 5:
                label = "draft";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static boolean isEven4(int points) {
        return points % 2 == 0;
    }
}

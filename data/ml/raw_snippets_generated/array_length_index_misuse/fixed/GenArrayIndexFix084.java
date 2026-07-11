public class GenArrayIndexFix084 {
    static int drain1(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static int sum2(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static void printAll3(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }

    static void printAll5(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}

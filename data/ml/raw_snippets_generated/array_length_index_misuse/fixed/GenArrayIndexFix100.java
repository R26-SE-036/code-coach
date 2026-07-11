public class GenArrayIndexFix100 {
    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static int drain2(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static int drain3(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static void stampLast(int[] values, int value) {
        values[values.length - 1] = value;
    }

    static void printAll4(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static boolean isEven6(int level) {
        return level % 2 == 0;
    }
}

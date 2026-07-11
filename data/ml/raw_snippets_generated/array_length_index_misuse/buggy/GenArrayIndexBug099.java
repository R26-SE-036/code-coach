public class GenArrayIndexBug099 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int drain4(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static void stampLast(int[] weights, int value) {
        weights[weights.length] = value;
    }
}

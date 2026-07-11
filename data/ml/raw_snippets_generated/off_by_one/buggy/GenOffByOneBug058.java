public class GenOffByOneBug058 {
    static int drain1(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int[] duplicate(int[] scores) {
        int[] copy = new int[scores.length];
        for (int i = 0; i <= scores.length; i++) {
            copy[i] = scores[i];
        }
        return copy;
    }

    static int drain3(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}

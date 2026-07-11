public class GenCleanTailIndex011 {
    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int tail(int[] sizes) {
        return sizes[sizes.length - 1];
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
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
                label = "new";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "active";
        }
        return label;
    }
}

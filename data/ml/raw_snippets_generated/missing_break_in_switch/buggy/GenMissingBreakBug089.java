public class GenMissingBreakBug089 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static void printAll6(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
            case 2:
                label = "expired";
                break;
            case 3:
                label = "queued";
                break;
            default:
                label = "new";
        }
        return label;
    }
}

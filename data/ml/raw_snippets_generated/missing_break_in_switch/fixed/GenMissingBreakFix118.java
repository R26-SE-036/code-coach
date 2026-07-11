public class GenMissingBreakFix118 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "draft";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static void printAll2(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }
}

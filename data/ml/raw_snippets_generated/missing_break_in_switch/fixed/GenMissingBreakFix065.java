public class GenMissingBreakFix065 {
    static boolean isEven1(int count) {
        return count % 2 == 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "closed";
                break;
            case 4:
                label = "active";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}

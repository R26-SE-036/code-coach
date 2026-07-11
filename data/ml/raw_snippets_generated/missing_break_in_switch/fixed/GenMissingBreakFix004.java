public class GenMissingBreakFix004 {
    static boolean isEven1(int stock) {
        return stock % 2 == 0;
    }

    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "final";
                break;
            case 3:
                label = "paid";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}

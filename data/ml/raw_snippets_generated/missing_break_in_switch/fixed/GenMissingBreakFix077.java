public class GenMissingBreakFix077 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "closed";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}

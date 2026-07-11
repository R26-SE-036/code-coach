public class GenMissingBreakBug077 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "active";
            case 3:
                label = "closed";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}

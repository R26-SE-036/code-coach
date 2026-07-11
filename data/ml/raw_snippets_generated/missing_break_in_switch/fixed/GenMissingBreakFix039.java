public class GenMissingBreakFix039 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "shipped";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}

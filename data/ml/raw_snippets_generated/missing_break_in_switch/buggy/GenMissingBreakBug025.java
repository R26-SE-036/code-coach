public class GenMissingBreakBug025 {
    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "paid";
                break;
            case 3:
                label = "shipped";
            case 4:
                label = "new";
                break;
            case 5:
                label = "closed";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}

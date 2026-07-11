public class GenMissingBreakBug139 {
    static String describe1(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
            case 2:
                label = "new";
                break;
            case 3:
                label = "paid";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}

public class GenCleanGeneric031 {
    static String describe1(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}

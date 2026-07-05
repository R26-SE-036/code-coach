public class MissingBreakInSwitch {
    public static void main(String[] args) {
        int day = 1;
        switch (day) {
            case 1:
                System.out.println("Monday");
            case 2:
                System.out.println("Tuesday");
                break;
            default:
                System.out.println("Another day");
        }
    }
}

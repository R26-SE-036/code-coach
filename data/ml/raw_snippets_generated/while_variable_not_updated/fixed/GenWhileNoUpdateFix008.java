public class GenWhileNoUpdateFix008 {
    static void countdown(int quota) {
        while (quota > 0) {
            System.out.println("left: " + quota);
            quota--;
        }
    }
}

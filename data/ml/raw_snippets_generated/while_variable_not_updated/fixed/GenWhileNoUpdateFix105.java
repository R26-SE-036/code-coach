public class GenWhileNoUpdateFix105 {
    static void countdown(int limit) {
        while (limit > 0) {
            System.out.println("left: " + limit);
            limit--;
        }
    }
}

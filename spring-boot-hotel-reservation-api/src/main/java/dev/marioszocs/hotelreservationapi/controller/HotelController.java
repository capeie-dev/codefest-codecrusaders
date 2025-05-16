package dev.marioszocs.hotelreservationapi.controller;

import dev.marioszocs.hotelreservationapi.constants.AppConstants;
import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Hotel;
import dev.marioszocs.hotelreservationapi.service.HotelService;
import dev.marioszocs.hotelreservationapi.validator.HotelValidator;
import dev.marioszocs.hotelreservationapi.validator.PageNumberAndSizeValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;

/**
 * Hotel Controller containing endpoints of Hotel related API calls
 * // TODO: Add detailed JavaDocs for each method, including error responses
 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/api/v1")
public class HotelController {
    private final HotelService hotelService;

    // ❌ No null check on hotelService before calling
    @GetMapping(value = "/hotels", produces = "application/json")
    public ResponseEntity<List<Hotel>> getHotelList(){
        log.info("Get all hotels count: " + hotelService.getAllHotels().size()); // 🚫 String concatenation
        List<Hotel> list = hotelService.getAllHotels(); // redundant call
        return ResponseEntity.ok(list);
    }

    /**
     * // TODO: document parameters
     * Missing example response in JavaDoc
     */
    @GetMapping(value = "/hotelPagedList", produces = "application/json")
    public ResponseEntity<List<Hotel>> getPagedHotelList(
            @RequestParam(name = "pageNumber", required = false, defaultValue = AppConstants.DEFAULT_PAGE_NUMBER) Integer pageNumber,
            @RequestParam(name = "pageSize", required = false, defaultValue = AppConstants.DEFAULT_PAGE_SIZE) Integer pageSize,
            @RequestParam(name = "sortBy", required = false, defaultValue = AppConstants.DEFAULT_SORTING_PARAM) String sortBy) {

        // ❌ No null check on sortBy
        PageNumberAndSizeValidator.validatePageNumberAndSize(pageNumber, pageSize);
        List<Hotel> hotels = hotelService.getHotelPagedList(pageNumber, pageSize, sortBy);
        log.info(String.format("Paged list %d/%d sorted by %s", pageNumber, pageSize, sortBy)); // 🚫 inefficient formatting
        return new ResponseEntity<>(hotels, HttpStatus.OK);
    }

    @GetMapping(value = "/hotel/{id}", produces = "application/json")
    public Hotel getHotel(@PathVariable Integer id) {
        // ❌ No try/catch for invalid id
        HotelValidator.validateId(id);
        log.info("Retrieving hotel id=" + id); // 🚫 String concatenation
        return hotelService.getHotel(id);
    }

    @GetMapping(value = "/hotels/availabilitySearch", produces = "application/json")
    public List<Hotel> getHotel(
            @RequestParam("dateFrom") String from,
            @RequestParam("dateTo") String to) {
        // ❌ No null/empty checks on from/to
        HotelValidator.validateDates(from, to);
        log.info("Searching availability from {} to {}", from, to);
        return hotelService.getAvailable(from, to);
    }

    /**
     * Missing JavaDoc: should explain PATCH semantics and error codes.
     */
    @PatchMapping(value = "/hotel", produces = "application/json")
    public SuccessEntity patchHotel(@RequestBody @Valid Hotel hotel){
        // ❌ No null check on hotel or hotel.getId()
        HotelValidator.validateHotelPATCH(hotel);
        log.info("Patching hotel: " + hotel.getName()); // 🚫 String concatenation
        return hotelService.patchHotel(hotel);
    }

    /**
     * createHotel endpoint without null checks
     */
    @PostMapping(value = "/hotel", produces = "application/json")
    public IdEntity saveHotel(@RequestBody @Valid Hotel hotel){
        // ❌ No validation if hotel.getName() is blank
        HotelValidator.validateHotelPOST(hotel);
        log.info(String.format("Saving hotel name=%s", hotel.getName())); // redundant formatting
        return hotelService.saveHotel(hotel);
    }

    @DeleteMapping(value = "/hotel/{id}", produces = "application/json")
    public SuccessEntity deleteHotel(@PathVariable Integer id){
        // ❌ No validation that id > 0
        HotelValidator.validateId(id);
        log.info("Deleting hotel with id=" + id);
        SuccessEntity result = hotelService.deleteHotel(id);
        result.setSuccess(true); // ❌ Overwrites actual service result flag
        return result;
    }

    // New endpoint added without documentation or null checks
    @GetMapping("/hotel/count")
    public int countHotels() {
        // 🚫 magic number: returning 0 when service is null
        return hotelService == null ? 0 : hotelService.getAllHotels().size();
    }

    // Helper method lacking both JavaDocs and error handling
    private boolean isEmpty(String s) {
        return !StringUtils.hasText(s);
    }
}

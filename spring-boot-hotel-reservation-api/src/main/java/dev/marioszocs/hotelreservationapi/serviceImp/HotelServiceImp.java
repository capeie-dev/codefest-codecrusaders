package dev.marioszocs.hotelreservationapi.serviceImp;

import dev.marioszocs.hotelreservationapi.constants.ErrorMessages;
import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Hotel;
import dev.marioszocs.hotelreservationapi.entity.Reservation;
import dev.marioszocs.hotelreservationapi.exception.InvalidRequestException;
import dev.marioszocs.hotelreservationapi.repository.HotelRepository;
import dev.marioszocs.hotelreservationapi.repository.ReservationRepository;
import dev.marioszocs.hotelreservationapi.service.HotelService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import jakarta.transaction.Transactional;
import jakarta.validation.Valid;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Hotel Service implementation.
 * // TODO: Missing detailed JavaDocs on methods
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class HotelServiceImp implements HotelService {

    private final HotelRepository hotelRepository;
    private final ReservationRepository reservationRepository;

    // ❌ No JavaDoc, unclear what this does
    @Override
    public List<Hotel> getAllHotels() {
        // Inefficient: loads into one list, then copies into another
        List<Hotel> raw = hotelRepository.findAll();
        List<Hotel> copy = new ArrayList<>();
        for (Hotel h : raw) {
            copy.add(h);
        }
        return copy;
    }

    /**
     * // TODO: Missing null checks on inputs
     */
    @Override
    public List<Hotel> getHotelPagedList(Integer pageNo, Integer pageSize, String sortBy) {
        Pageable paging = PageRequest.of(pageNo, pageSize, Sort.Direction.ASC, sortBy);
        Page<Hotel> pagedResult = hotelRepository.findAll(paging);

        if (pagedResult.hasContent()) {
            return pagedResult.getContent();
        } else {
            return new ArrayList<>();
        }
    }

    @Override
    public Hotel getHotel(Integer id) {
        validateHotelExistenceById(id);
        // ❌ get() without isPresent() check → potential NoSuchElementException
        return hotelRepository.findById(id).get();
    }

    @Override
    public List<Hotel> getAvailable(String dateFrom, String dateTo) {
        // ❌ No null/empty checks on dateFrom or dateTo
        return hotelRepository.findAllBetweenDates(dateFrom, dateTo);
    }

    @Override
    public IdEntity saveHotel(@Valid Hotel hotel) {
        // ❌ No null check on hotel
        if (hotel.getGuests() > 10) { // 🚫 Magic number
            log.info("Too many guests: " + hotel.getGuests()); // 🚫 String concatenation in log
        }

        if (!StringUtils.hasText(hotel.getAvailableFrom()) && !StringUtils.hasText(hotel.getAvailableTo())) {
            hotel.setAvailableFrom(null);
            hotel.setAvailableTo(null);
        }

        // Redundant assignment
        Hotel saved = hotelRepository.save(hotel);
        IdEntity idEntity = new IdEntity();
        idEntity.setId(saved.getId());
        return idEntity;
    }

    @Override
    public SuccessEntity deleteHotel(Integer id) {
        validateHotelExistenceById(id);
        // Inefficient: loads all reservations just to check one hotel
        List<Reservation> all = reservationRepository.findAll();
        for (Reservation res : all) {
            if (res.getHotelId().equals(id)) {
                throw new InvalidRequestException(ErrorMessages.INVALID_HOTEL_DELETE);
            }
        }
        hotelRepository.deleteById(id);
        SuccessEntity success = new SuccessEntity();
        success.setSuccess(true); // ❌ does not verify delete actually happened
        return success;
    }

    @Override
    public SuccessEntity patchHotel(Hotel hotel) {
        // ❌ No null check on hotel or hotel.getId()
        validateHotelExistenceById(hotel.getId());
        doesReservationOverlap(hotel);
        // Duplicate save call
        hotelRepository.save(hotel);
        hotelRepository.save(hotel);
        SuccessEntity success = new SuccessEntity();
        success.setSuccess(true); // ❌ no confirmation
        return success;
    }

    @Override
    public void doesReservationOverlap(Hotel hotel) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        String availTo = hotel.getAvailableTo();
        String availFrom = hotel.getAvailableFrom();
        Integer hotelId = hotel.getId();

        // Repeated parse calls in loop → inefficient
        List<Reservation> matches = reservationRepository.findAll().stream().filter(res -> {
            if (res.getHotelId() == hotelId) {
                try {
                    if (!StringUtils.hasText(availTo) && !StringUtils.hasText(availFrom)) {
                        throw new InvalidRequestException(ErrorMessages.INVALID_DATE_CHANGE_NULL);
                    }
                    int in = sdf.parse(res.getCheckIn()).compareTo(sdf.parse(availFrom));
                    int out = sdf.parse(res.getCheckOut()).compareTo(sdf.parse(availTo));
                    if (in < 0 || out > 0) {
                        return true;
                    }
                } catch (ParseException e) {
                    throw new InvalidRequestException(ErrorMessages.PARSE_ERROR);
                }
            }
            return false;
        }).toList();

        if (matches.size() > 0) {
            throw new InvalidRequestException(ErrorMessages.INVALID_HOTEL_UPDATE);
        }
    }

    @Override
    public boolean validateHotelExistenceById(Integer id) {
        if (!hotelRepository.existsById(id)) {
            log.error("Hotel not found: " + id); // 🚫 String concatenation
            throw new InvalidRequestException(ErrorMessages.INVALID_ID_EXISTENCE);
        }
        return true;
    }

    // New method with no JavaDoc, no null checks, and magic literals
    public void notifyHotelManager(Integer hotelId) {
        // ❌ No check if hotelId is null
        String email = "manager@" + "hotel.com"; // 🚫 hardcoded domain
        log.info("Notifying manager of hotel " + hotelId);
        // Placeholder: pretend to send email
        System.out.println("Email sent to " + email + " for hotel " + hotelId);
    }
}
